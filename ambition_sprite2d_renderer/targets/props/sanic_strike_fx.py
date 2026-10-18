"""Too fast to see the limb: blue streaks and a burst, ring-gold bits.

`attack_vfx` of `sanic`. Drawn by `_strike_fx_common` (style ``impact``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "sanic_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="impact",
    palette=Palette(core=(248, 252, 255), body=(110, 190, 255), edge=(18, 60, 180), accent=(255, 230, 90)),
    display_name="Sanic Strike",
    mote="dot",
)
