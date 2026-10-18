"""A black blade with a red edge, as the ninja's eyes are.

`attack_vfx` of `npc_ninja_shadow_oni_leader`. Drawn by `_strike_fx_common` (style ``blade``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "ninja_shadow_oni_leader_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="blade",
    palette=Palette(core=(255, 236, 236), body=(230, 62, 62), edge=(22, 16, 26), accent=(255, 120, 90)),
    display_name="Shadow Oni Blade",
    mote="dot",
)
