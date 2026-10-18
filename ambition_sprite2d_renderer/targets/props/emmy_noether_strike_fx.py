"""A violet ribbon of symmetry that sheds four-pointed stars.

`attack_vfx` of `npc_emmy_noether`. Drawn by `_strike_fx_common` (style ``energy``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "emmy_noether_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="energy",
    palette=Palette(core=(255, 255, 255), body=(196, 176, 255), edge=(76, 56, 160), accent=(236, 226, 255)),
    display_name="Emmy Noether Strike",
    mote="star",
)
