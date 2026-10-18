"""Alice's blows: a pink streak and burst.

`attack_vfx` of `npc_alice`. Drawn by `_strike_fx_common` (style ``impact``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "alice_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="impact",
    palette=Palette(core=(255, 250, 255), body=(240, 168, 222), edge=(126, 44, 132), accent=(255, 214, 240)),
    display_name="Alice Strike",
    mote="dot",
)
