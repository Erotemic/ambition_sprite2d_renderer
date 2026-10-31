"""The void Projectile Polygon's blow: a white arc on the black of the void.

`attack_vfx` of `void_projectile_polygon`. The style of `projectile_polygon_strike_fx`
(`arc`), in the void's palette: a white core, a grey body and a near-black
edge, so the strike reads on the void's white and on its black.
"""

from __future__ import annotations

from ._strike_fx_common import Palette, renderer, sheet_files

TARGET_NAME = "void_projectile_polygon_strike_fx"
SHEET_FILES = sheet_files(TARGET_NAME)

render, ACTOR_METADATA = renderer(
    TARGET_NAME,
    style="arc",
    palette=Palette(core=(255, 255, 255), body=(200, 200, 208), edge=(18, 18, 24), accent=(240, 240, 246)),
    display_name="Void Projectile Polygon Strike",
    mote="dot",
)
