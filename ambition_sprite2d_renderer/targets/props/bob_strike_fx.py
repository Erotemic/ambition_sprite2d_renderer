"""Bob's blows: a green streak and burst.

`attack_vfx` of `npc_bob`. Drawn by `_strike_fx_common` (style ``impact``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "bob_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="impact",
    palette=Palette(core=(248, 255, 246), body=(160, 226, 150), edge=(36, 112, 58), accent=(214, 255, 190)),
    display_name="Bob Strike",
    mote="dot",
)
