"""Chalk-gold, as his symbols are written: a ribbon shedding dashes of chalk.

`attack_vfx` of `npc_ramen_nujan`. Drawn by `_strike_fx_common` (style ``energy``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "ramen_nujan_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="energy",
    palette=Palette(core=(255, 250, 222), body=(240, 208, 104), edge=(116, 86, 28), accent=(255, 240, 190)),
    display_name="Ramen-nujan Strike",
    mote="chalk",
)
