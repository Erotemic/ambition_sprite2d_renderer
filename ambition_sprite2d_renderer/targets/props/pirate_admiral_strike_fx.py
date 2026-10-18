"""The cutlass: a steel crescent with a navy edge, gold sparks off it.

`attack_vfx` of `npc_pirate_admiral`. Drawn by `_strike_fx_common` (style ``blade``);
this module states only whose blow it is.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "pirate_admiral_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="blade",
    palette=Palette(core=(248, 249, 242), body=(210, 216, 228), edge=(52, 62, 92), accent=(244, 220, 132)),
    display_name="Pirate Admiral Cutlass",
    mote="dot",
)
