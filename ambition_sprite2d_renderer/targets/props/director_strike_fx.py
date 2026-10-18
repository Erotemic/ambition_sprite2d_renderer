"""The fountain pen: a stroke of ink with a brass light in it, red where it spatters.

`attack_vfx` of `director`. Drawn by `_strike_fx_common` (style ``ink``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "director_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="ink",
    palette=Palette(core=(255, 250, 232), body=(236, 196, 116), edge=(34, 30, 58), accent=(196, 48, 40)),
    display_name="Director Strike",
    mote="dot",
)
