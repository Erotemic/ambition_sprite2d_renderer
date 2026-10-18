"""A green ribbon that sheds square cells. Kept light: his sheet already bakes its own blasts.

`attack_vfx` of `perfect_cellular_automaton`. Drawn by `_strike_fx_common` (style ``energy``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "perfect_cellular_automaton_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="energy",
    palette=Palette(core=(242, 255, 226), body=(150, 226, 96), edge=(36, 98, 40), accent=(210, 255, 170)),
    display_name="Perfect Cellular Automaton Strike",
    mote="cell",
)
