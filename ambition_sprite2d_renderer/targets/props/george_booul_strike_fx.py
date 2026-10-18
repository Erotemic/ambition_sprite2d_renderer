"""A stroke of logic in blue-black ink on his paper's white, gold where it spatters: he argues with a pen.

`attack_vfx` of `smash_george_booul`. Drawn by `_strike_fx_common` (style ``ink``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "george_booul_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="ink",
    palette=Palette(core=(252, 250, 240), body=(214, 220, 240), edge=(40, 46, 96), accent=(232, 196, 92)),
    display_name="George Booul Strike",
    mote="dot",
)
