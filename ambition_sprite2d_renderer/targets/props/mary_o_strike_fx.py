"""A punch or a stomp: speed streaks in her red and a yellow star where it lands.

`attack_vfx` of `mary_o_tall`. Drawn by `_strike_fx_common` (style ``impact``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "mary_o_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="impact",
    palette=Palette(core=(255, 255, 244), body=(255, 214, 84), edge=(196, 36, 36), accent=(255, 244, 170)),
    display_name="Mary-O Strike",
    mote="dot",
)
