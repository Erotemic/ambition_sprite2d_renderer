"""Billions of stars: a deep-space ribbon shedding stars.

`attack_vfx` of `npc_carl_stargan`. Drawn by `_strike_fx_common` (style ``energy``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "carl_stargan_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="energy",
    palette=Palette(core=(255, 255, 255), body=(170, 204, 255), edge=(56, 40, 126), accent=(255, 240, 190)),
    display_name="Carl Stargan Strike",
    mote="star",
)
