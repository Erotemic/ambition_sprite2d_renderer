"""Light, bent: a golden ribbon shedding photons.

`attack_vfx` of `special_patent_clerk`. Drawn by `_strike_fx_common` (style ``energy``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "patent_clerk_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="energy",
    palette=Palette(core=(255, 255, 246), body=(255, 238, 150), edge=(176, 112, 36), accent=(255, 250, 210)),
    display_name="Patent Clerk Strike",
    mote="dot",
)
