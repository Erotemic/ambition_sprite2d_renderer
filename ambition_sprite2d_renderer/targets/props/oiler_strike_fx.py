"""Warm orange curves, as his formulas are drawn.

`attack_vfx` of `npc_oiler`. Drawn by `_strike_fx_common` (style ``energy``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "oiler_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="energy",
    palette=Palette(core=(255, 250, 236), body=(255, 196, 110), edge=(150, 72, 22), accent=(255, 232, 180)),
    display_name="Oiler Strike",
    mote="dot",
)
