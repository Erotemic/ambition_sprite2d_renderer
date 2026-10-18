"""A heavy club blow: a moss-green streak and burst.

`attack_vfx` of `goblin`. Drawn by `_strike_fx_common` (style ``impact``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "goblin_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="impact",
    palette=Palette(core=(250, 246, 214), body=(178, 204, 84), edge=(66, 86, 28), accent=(236, 224, 140)),
    display_name="Goblin Strike",
    mote="dot",
)
